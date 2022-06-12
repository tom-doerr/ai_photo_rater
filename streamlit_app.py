import streamlit as st
import time
from clip_client import Client
from docarray import Document
import os

# photo upload

IMAGES_FOLDER = 'images'

os.makedirs(IMAGES_FOLDER, exist_ok=True)

# photo_file = st.file_uploader("Upload a photo", type=["jpg", "png"])
photo_file = st.file_uploader("Upload a photo")

if not photo_file:
    st.write("Please upload a photo")
    st.stop()

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
    fig = go.Figure(data=[go.Bar(x=[label], y=[score*100])])
    # range 0 to 100 for the y axis:
    fig.update_layout(yaxis=dict(range=[0, 100]))

    st.plotly_chart(fig)




# score = rate_image(filename_path, 'the person is pretty', 'the person is ugly')
create_analysis(filename_path, 'the person is pretty', 'the person is ugly', 'Beauty')
create_analysis(filename_path, 'the person is trustworthy', 'the person is dishonest', 'Trustworthiness')
create_analysis(filename_path, 'the person is smart', 'the person is stupid', 'Intelligence')

