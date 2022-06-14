import streamlit as st
import time
from clip_client import Client
from docarray import Document
import os

# photo upload

IMAGES_FOLDER = 'images'
PAGE_LOAD_LOG_FILE = 'page_load_log.txt'
METRIC_TEXTS = {
    'Attractivness': ('this person is attractive', 'this person is unattractive'),
    'Hotness': ('this person is hot', 'this person is ugly'),
    'Trustworthiness': ('this person is trustworthy', 'this person is dishonest'),
    'Intelligence': ('this person is smart', 'this person is stupid'),
    'Quality': ('this image looks good', 'this image looks bad'),
}

st.set_page_config(page_title='AI Photo Rater', initial_sidebar_state="auto")


st.title('AI Photo Rater')

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



def show_sidebar_metrics():
    metric_options = list(METRIC_TEXTS.keys())
    default_metrics = ['Attractivness', 'Trustworthiness', 'Intelligence'] 
    st.sidebar.title('Metrics')
    # metric = st.sidebar.selectbox('Select a metric', metric_options)
    selected_metrics = []
    for metric in metric_options:
        selected = metric in default_metrics
        if st.sidebar.checkbox(metric, selected):
            selected_metrics.append(metric)

    with st.sidebar.expander('Metric texts'):
        st.write(METRIC_TEXTS)

    print("selected_metrics:", selected_metrics)
    return selected_metrics


def get_custom_metric():
    st.sidebar.markdown('**Custom metric**:')
    metric_name = st.sidebar.text_input('Metric name', placeholder='e.g. "Youth"')
    metric_target = st.sidebar.text_input('Metric target', placeholder='this person is young')
    metric_opposite = st.sidebar.text_input('Metric opposite', placeholder='this person is old')
    return {metric_name: (metric_target, metric_opposite)}




log_page_load()

metrics = show_sidebar_metrics()
st.sidebar.markdown('---')
custom_metric = get_custom_metric()
st.sidebar.markdown('---')
st.sidebar.write(f'Page loads: {get_num_page_loads()}')
st.sidebar.write(f'Earliest page load: {get_earliest_page_load_time()}')

metric_texts = METRIC_TEXTS
print("custom_metric:", custom_metric)
custom_key = list(custom_metric.keys())[0]
if custom_key:
    custom_tuple = custom_metric[custom_key]
    if custom_tuple[0] and custom_tuple[1]:
        metrics.append(list(custom_metric.keys())[0])
        metric_texts = {**metric_texts, **custom_metric}

os.makedirs(IMAGES_FOLDER, exist_ok=True)

# photo_file = st.file_uploader("Upload a photo", type=["jpg", "png"])
photo_files = st.file_uploader("Upload a photo", accept_multiple_files=True)
# sort them
photo_files = sorted(photo_files, key=lambda x: x.name)

if not photo_files:
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


# @st.cache
def process_image(photo_file, metrics):
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
        scores = dict()
        for metric in metrics:
            target = metric_texts[metric][0]
            opposite = metric_texts[metric][1]
            score = rate_image(filename_path, target, opposite)
            scores[metric] = score


        scores['Avg'] = sum(scores.values()) / len(scores)

        # plot them
        import plotly.graph_objects as go


        scores_percent = []
        for metric in metrics:
            scores_percent.append(scores[metric] * 100)
        fig = go.Figure(data=[go.Bar(x=metrics, y=scores_percent)], layout=go.Layout(title='Scores'))
        # range 0 to 100 for the y axis:
        fig.update_layout(yaxis=dict(range=[0, 100]))

        st.plotly_chart(fig, use_container_width=True)

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
    filename_path, scores = process_image(photo_file, metrics)
    # image_scores_list.append((filename_path, scores))
    image_scores_list.append((photo_file, scores))
    st.markdown('---')


if len(photo_files) > 1:
    st.title('Best image')
    metric = st.selectbox('Select a metric', ['Avg'] + metrics)
    image_file = get_best_image(image_scores_list, metric)
    # st.image(image_file, use_column_width=True)
    # from PIL import Image
    # image_file = Image.open(image_path)
    process_image(image_file, metrics)


st.markdown('---')

col1, col2, col3 = st.columns([10,10,10])
with col1:
    st.markdown('[GiHub Repo](https://github.com/tom-doerr/ai_photo_rater)')

with col2:
    st.markdown('Powered by [Jina.ai](https://jina.ai/)')
