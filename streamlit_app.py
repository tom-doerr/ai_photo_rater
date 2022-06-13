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
photo_files = st.file_uploader("Upload a photo", accept_multiple_files=True)

if not photo_files:
    st.write("Please upload a photo")
    st.stop()



c = Client('grpcs://demo-cas.jina.ai:2096')


@st.cache(show_spinner=False)
def rate_image(image_path, target, opposite, attempt=0):
    try:
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
    except ConnectionError as e:
        print(e)
        print(f'Retrying... {attempt}')
        time.sleep(2**attempt)
        return rate_image(image_path, target, opposite, attempt + 1)
    text_and_scores = r['@m', ['text', 'scores__clip_score__value']]
    index_of_good_text = text_and_scores[0].index(target)
    score =  text_and_scores[1][index_of_good_text]
    return score



def process_image(photo_file):
    col1, col2, col3 = st.columns([10,10,10])
    with st.spinner('Loading...'):
        with col1:
            st.write('')
        with col2:
            st.image(photo_file, use_column_width=True)
        with col3:
            st.write('')


    # save it
    filename = f'{time.time()}'.replace('.', '_')
    filename_path = f'{IMAGES_FOLDER}/{filename}'
    with open(f'{filename_path}', 'wb') as f:
        f.write(photo_file.read())






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

    scores = {
        'beauty': score_beauty,
        'trustworthiness': score_trustworthiness,
        'intelligence': score_intelligence,
        'avg': (score_beauty + score_trustworthiness + score_intelligence) / 3
    }
    return filename_path, scores


def get_best_image(image_scores_list, metric):
    best_image = image_scores_list[0][0]
    best_score = image_scores_list[0][1][metric]
    for image, scores in image_scores_list[2:]:
        if scores[metric] > best_score:
            best_image = image
            best_score = scores[metric]
    return best_image




image_scores_list = []
for photo_file in photo_files:
    # process_image(photo_file)
    filename_path, scores = process_image(photo_file)
    # image_scores_list.append((filename_path, scores))
    image_scores_list.append((photo_file, scores))
    st.markdown('---')


if len(photo_files) > 1:
    st.title('Best image')
    metric = st.selectbox('Select a metric', ['avg', 'beauty', 'trustworthiness', 'intelligence'])
    image_file = get_best_image(image_scores_list, metric)
    # st.image(image_file, use_column_width=True)
    # from PIL import Image
    # image_file = Image.open(image_path)
    process_image(image_file)
