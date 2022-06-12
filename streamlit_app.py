import streamlit as st
import time
from clip_client import Client
from docarray import Document
import os

# photo upload

IMAGES_FOLDER = 'images'
PAGE_LOAD_LOG_FILE = 'page_load_log.txt'

st.set_page_config(page_title='Photo Rating AI', initial_sidebar_state="collapsed")



def log_page_load():
    with open(PAGE_LOAD_LOG_FILE, 'a') as f:
        f.write(f'{time.time()}\n')


def get_num_page_loads():
    with open(PAGE_LOAD_LOG_FILE, 'r') as f:
        return len(f.readlines())

def get_earliest_page_load_time():
    with open(PAGE_LOAD_LOG_FILE, 'r') as f:
        lines = f.readlines()
        unix_time = float(lines[0])

    date_string = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(unix_time))
    return date_string







log_page_load()
st.sidebar.write(f'Page loads: {get_num_page_loads()}')
st.sidebar.write(f'Earliest page load: {get_earliest_page_load_time()}')

os.makedirs(IMAGES_FOLDER, exist_ok=True)

# photo_file = st.file_uploader("Upload a photo", type=["jpg", "png"])
photo_file = st.file_uploader("Upload a photo")

if not photo_file:
    st.write("Please upload a photo")
    st.stop()


col1, col2, col3 = st.columns([10,10,10])
with st.spinner('Loading...'):
    with col2:
        st.image(photo_file, use_column_width=True)


# save it
filename = f'{time.time()}'.replace('.', '_')
filename_path = f'{IMAGES_FOLDER}/{filename}'
with open(f'{filename_path}', 'wb') as f:
    f.write(photo_file.read())



c = Client('grpcs://demo-cas.jina.ai:2096')

# r = c.rank(
    # [
        # Document(
            # # uri='https://www.pngall.com/wp-content/uploads/12/Britney-Spears-PNG-Image-File.png',
            # # uri='britney2.png',
            # uri=filename_path,
            # matches=[
                # Document(text=f'the person is {p}')
                # for p in (
                        # 'pretty',
                        # 'ugly',
                # )
            # ],
        # )
    # ]
# )

# text_and_scores = r['@m', ['text', 'scores__clip_score__value']]
# st.write(text_and_scores)


def rate_image(image_path, target, opposite):
    r = c.rank(
        [
            Document(
                # uri='https://www.pngall.com/wp-content/uploads/12/Britney-Spears-PNG-Image-File.png',
                uri=image_path,
                matches=[
                    Document(text=target),
                    Document(text=opposite),
                ],
            )
        ]
    )
    text_and_scores = r['@m', ['text', 'scores__clip_score__value']]
    index_of_good_text = text_and_scores[0].index(target)
    score =  text_and_scores[1][index_of_good_text]
    return score


def create_analysis(filename, target, opposite, label):
    score = rate_image(filename_path, target, opposite)
    # st.write(score)

    # st.write(f'The score is {score}')

    import plotly.graph_objects as go

    # same plot just showing beauty in percentage
    fig = go.Figure(data=[go.Bar(x=[label], y=[score*100])], layout=go.Layout(title=f'{label}'))
    # range 0 to 100 for the y axis:
    fig.update_layout(yaxis=dict(range=[0, 100]))

    st.plotly_chart(fig, use_container_width=True)




# score = rate_image(filename_path, 'the person is pretty', 'the person is ugly')

if False:
    col1, col2, col3 = st.columns([10,10,10])
    with col1:
        create_analysis(filename_path, 'the person is pretty', 'the person is ugly', 'Beauty')

    with col2:
        create_analysis(filename_path, 'the person is trustworthy', 'the person is dishonest', 'Trustworthiness')

    with col3:
        create_analysis(filename_path, 'the person is smart', 'the person is stupid', 'Intelligence')




with st.spinner('Rating your photo...'):
    score_beauty = rate_image(filename_path, 'the person is pretty', 'the person is ugly')
    score_trustworthiness = rate_image(filename_path, 'the person is trustworthy', 'the person is dishonest')
    score_intelligence = rate_image(filename_path, 'the person is smart', 'the person is stupid')


    # plot them
    import plotly.graph_objects as go


    fig = go.Figure(data=[go.Bar(x=['Beauty', 'Trustworthiness', 'Intelligence'], y=[score_beauty*100, score_trustworthiness*100, score_intelligence*100])], layout=go.Layout(title='Scores'))
    # range 0 to 100 for the y axis:
    fig.update_layout(yaxis=dict(range=[0, 100]))

    st.plotly_chart(fig, use_container_width=True)



