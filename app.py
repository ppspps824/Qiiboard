import json
import urllib.request

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from janome.tokenizer import Tokenizer
from PIL import Image
from wordcloud import WordCloud


def hide_style():
    hide_streamlit_style = """
                    <style>
                    div[data-testid="stToolbar"] {
                    visibility: hidden;
                    height: 0%;
                    position: fixed;
                    }
                    div[data-testid="stDecoration"] {
                    visibility: hidden;
                    height: 0%;
                    position: fixed;
                    }
                    div[data-testid="stStatusWidget"] {
                    visibility: hidden;
                    height: 0%;
                    position: fixed;
                    }
                    #MainMenu {
                    visibility: hidden;
                    height: 0%;
                    }
                    header {
                    visibility: hidden;
                    height: 0%;
                    }
                    footer {
                    visibility: hidden;
                    height: 0%;
                    }
                    .block-container {
                    padding-top: 2rem;
                    }
                    </style>
                    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def get_word_str(text):
    word_list = []
    t = Tokenizer()
    for token in t.tokenize(text):
        split_token = token.part_of_speech.split(",")
        ## 一般名詞を抽出
        if split_token[0] == "名詞" and split_token[1] == "一般":
            word_list.append(token.surface)
    split_text = " ".join(word_list)
    return split_text


@st.cache_data(experimental_allow_widgets=True, show_spinner=False)
def show_wordcloud(text):
    with st.spinner("Wordcloud作成中・・・"):
        # Create some sample text
        split_text = get_word_str(text)

        # Create and generate a word cloud image:
        wordcloud = WordCloud(
            font_path="ipaexg.ttf", background_color="white"
        ).generate(split_text)

        # Display the generated image:
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        st.pyplot(plt)


# クエリパラメータを組み立てる(1ページ100件固定)
def prepare_parameter(query):
    params = {"per_page": "100"}
    if query is not None:
        params["query"] = query

    return params


# 認証トークンが指定された場合にヘッダに付与する
def prepare_headers(token):
    req_headers = {}
    if token is not None:
        req_headers = {"Authorization": "Bearer " + token}

    return req_headers


def create_metric(
    wch_colour_box=(87, 204, 0),
    wch_colour_font=(255, 255, 255),
    fontsize=36,
    valign="left",
    iconname="fas fa-asterisk",
    sline="",
    value="",
):
    lnk = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" crossorigin="anonymous">'

    htmlstr = f"""<p style='background-color: rgb({wch_colour_box[0]}, 
                                                {wch_colour_box[1]}, 
                                                {wch_colour_box[2]}, 1); 
                            color: rgb({wch_colour_font[0]}, 
                                    {wch_colour_font[1]}, 
                                    {wch_colour_font[2]}, 1); 
                            font-size: {fontsize}px; 
                            border-radius: 7px; 
                            padding-left: 12px; 
                            padding-top: 18px; 
                            padding-bottom: 18px; 
                            line-height:25px;'>
                            <i class='{iconname} fa-xs'></i> {value}
                            <BR><span style='font-size: 14px; 
                            margin-top: 0;'>{sline}</style></span>
                            </style></p>"""

    st.markdown(lnk + htmlstr, unsafe_allow_html=True)


def show_articles(value):
    create_metric(sline="Articles", value=value, iconname="fa fa-newspaper")


def show_view_total(value):
    create_metric(sline="Views", value=value, iconname="fa fa-eye")


def show_likes_total(value):
    create_metric(sline="Likes", value=value, iconname="fa fa-thumbs-up")


def show_stocks_total(value):
    create_metric(sline="Stocks", value=value, iconname="fa fa-bookmark")


def show_comments_total(value):
    create_metric(sline="Comments", value=value, iconname="fa fa-comment")


def pagenation_by_total_likes(item_ids, token=None, query=None):
    df_likes = pd.DataFrame()
    # クエリパラメータの準備
    params = prepare_parameter(query)
    # アクセストークンが指定された場合に付与
    req_headers = prepare_headers(token)

    for num, item_id in enumerate(item_ids):
        with st.spinner(f"記事ごとの情報を取得中：{num+1}/{len(item_ids)}"):
            for page_num_likes in range(1, 101):
                params["page"] = str(page_num_likes)
                url_likes = (
                    f"https://qiita.com/api/v2/items/{item_id}/likes?"
                    + urllib.parse.urlencode(params)
                )

                req_likes = urllib.request.Request(url_likes, headers=req_headers)

                with urllib.request.urlopen(req_likes) as res_likes:
                    # DataFrameに記事情報を格納
                    df = pd.json_normalize(json.load(res_likes))
                    df["id"] = item_id
                    df_likes = pd.concat([df_likes, df])
                    print("Page: " + str(page_num_likes))
                    # Total-Countヘッダの値から最後のページまで取得したかを判断
                    total_count_likes = int(res_likes.headers["Total-Count"])
                    if page_num_likes >= (total_count_likes + 99) // 100:
                        break
    if len(df_likes):
        df_likes["created_at"] = df_likes["created_at"].str[0:13] + ":00:00"
        df_likes["created_at"] = pd.to_datetime(df_likes["created_at"])
        df_likes["created_at"] = df_likes["created_at"].dt.strftime("%Y/%m/%d")

    st.session_state.df_likes = df_likes


@st.cache_data(show_spinner=False)
def pagenation_by_total_count(token=None, query=None):
    df_ret = pd.DataFrame()

    # クエリパラメータの準備
    params = prepare_parameter(query)
    # アクセストークンが指定された場合に付与
    req_headers = prepare_headers(token)

    for page_num in range(1, 101):
        with st.spinner(f"記事情報取得中：{page_num}"):
            params["page"] = str(page_num)
            url = "https://qiita.com/api/v2/items?" + urllib.parse.urlencode(params)

            req = urllib.request.Request(url, headers=req_headers)
            with urllib.request.urlopen(req) as res:
                body = json.load(res)
                # DataFrameに記事情報を格納
                df = pd.json_normalize(body)
                df_ret = pd.concat([df_ret, df])
                print("Page: " + str(page_num))
                # Total-Countヘッダの値から最後のページまで取得したかを判断
                total_count = int(res.headers["Total-Count"])
                if page_num >= (total_count + 99) // 100:
                    break
    item_ids = df_ret["id"].to_list()

    return df_ret, item_ids


@st.cache_data(show_spinner=False)
def get_user_info(token, user_name):
    url = f"https://qiita.com/api/v2/users/{urllib.parse.quote(user_name)}"
    req_headers = prepare_headers(token)

    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req) as res:
            body = json.load(res)
    except urllib.error.HTTPError as err:
        st.error("ユーザ情報を取得できませんでした。")
        st.stop()
    return body


@st.cache_data(show_spinner=False)
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode("utf-8")


def main():
    st.set_page_config(
        page_title="Qiiboard", page_icon=Image.open("favicon.png"), layout="wide"
    )
    hide_style()

    if "df_likes" not in st.session_state:
        st.session_state.df_total_count = pd.DataFrame()
        st.session_state.df_likes = pd.DataFrame()

    sort_options = {
        "📝作成日": "created_at",
        "👍いいね数": "likes_count",
        "📚ストック数": "stocks_count",
        "👀閲覧数": "page_views_count",
        "💬コメント数": "comments_count",
    }

    with st.sidebar:
        with st.form("info"):
            user_name = st.text_input("User Name", placeholder="User Name")
            st.form_submit_button("データ取得")
        with st.expander("独自のAccess Tokenを利用する"):
            accsess_token = st.text_input(
                "独自のAccess Tokenを利用する",
                placeholder="Your Access Token",
                help="利用制限に引っかかっている場合、独自のアクセストークンを利用できます。",
            )
            st.write(
                "[アクセストークンの取得方法](https://github.com/ppspps824/Qiiboard#%E3%82%A2%E3%82%AF%E3%82%BB%E3%82%B9%E3%83%88%E3%83%BC%E3%82%AF%E3%83%B3%E3%81%AE%E5%8F%96%E5%BE%97%E6%96%B9%E6%B3%95)"
            )

        dl_place = st.container()

    if not accsess_token:
        accsess_token = st.secrets["QIITA_API_ACCESS_TOKEN"]

    st.image("logo.png")
    if user_name:
        if user_info := get_user_info(accsess_token, user_name):
            html = f"""
            <style>
            .avatar {{
            vertical-align: middle;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            }}  
            </style>

            <h2>
            <a href="https://qiita.com/{user_name}"><img src="{user_info['profile_image_url']}" alt="Avatar" class="avatar"></a>
            {user_name}
            </h2>
            """

            st.write("---")
            st.write(html, unsafe_allow_html=True)
            # Total-Countヘッダを利用して、「QiitaAPI」タグの記事を取得
            st.session_state.df_total_count, item_ids = pagenation_by_total_count(
                token=accsess_token, query=f"user:{user_name}"
            )
            df_total_count = st.session_state.df_total_count
            df_total_count["created_at"] = pd.to_datetime(df_total_count["created_at"])
            df_total_count["created_at"] = df_total_count["created_at"].dt.strftime(
                "%Y/%m/%d %H:%M:%S"
            )
            body_list = df_total_count["body"].to_list()
            title_list = df_total_count["title"].to_list()

            word_list = body_list + title_list
            wordcloud_text = "".join(word_list)

            articles = f"{len(df_total_count):,}"
            view_total = f'{df_total_count["page_views_count"].sum():,}'
            likes_total = f'{df_total_count["likes_count"].sum():,}'
            stocks_total = f'{df_total_count["stocks_count"].sum():,}'
            comments_total = f'{df_total_count["comments_count"].sum():,}'

            cols = st.columns(5)
            with cols[0]:
                show_articles(articles)
            with cols[1]:
                show_view_total(view_total)
            with cols[2]:
                show_likes_total(likes_total)
            with cols[3]:
                show_stocks_total(stocks_total)
            with cols[4]:
                show_comments_total(comments_total)

            show_wordcloud(wordcloud_text)

            with dl_place:
                st.write("---")
                st.download_button(
                    "記事一覧データを保存(CSV)",
                    data=convert_df(st.session_state.df_total_count),
                    file_name="qiiboard_articles.csv",
                    mime="text/csv",
                )

            if len(st.session_state.df_likes):
                df_likes = st.session_state.df_likes
                st.write("## Details")
                sort_value_jp = st.selectbox("Sort", options=sort_options.keys())

                for id, sdf in df_total_count.sort_values(
                    sort_options[sort_value_jp], ascending=False
                ).groupby("id", sort=False):
                    likes = pd.DataFrame()

                    if len(df_likes):
                        likes = (
                            df_likes[df_likes["id"] == id][["created_at", "id"]]
                            .groupby("created_at")
                            .count()
                        )
                        likes["likes"] = likes["id"].cumsum()
                        likes = likes.drop("id", axis=1)

                    title = sdf["title"].values[0]
                    title_caption = sdf[sort_options[sort_value_jp]].values[0]
                    with st.expander(f"【{sort_value_jp} / {title_caption}】\t{title} "):
                        st.write(
                            f'<a href="{sdf["url"].values[0]}">{title}</a>',
                            unsafe_allow_html=True,
                        )
                        cols = st.columns(4)
                        with cols[0]:
                            show_view_total(sdf["page_views_count"].values[0])
                        with cols[1]:
                            show_likes_total(sdf["likes_count"].values[0])
                        with cols[2]:
                            show_stocks_total(sdf["stocks_count"].values[0])
                        with cols[3]:
                            show_comments_total(sdf["comments_count"].values[0])
                        st.line_chart(likes)

                with dl_place:
                    st.download_button(
                        "いいねデータを保存(CSV)",
                        data=convert_df(st.session_state.df_likes),
                        file_name="qiiboard_likes.csv",
                        mime="text/csv",
                    )
            else:
                if st.button("記事ごとの情報を取得する", help="取得に時間がかかる場合があります。"):
                    pagenation_by_total_likes(
                        item_ids, accsess_token, f"user:{user_name}"
                    )
                    st.experimental_rerun()

    else:
        st.info(
            "ユーザー名を入力してください。",
            icon="👈",
        )
if __name__ == "__main__":
    main()
