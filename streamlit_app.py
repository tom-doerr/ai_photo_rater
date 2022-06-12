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

r = c.rank(
    [
        Document(
            # uri='https://www.pngall.com/wp-content/uploads/12/Britney-Spears-PNG-Image-File.png',
            # uri='britney2.png',
            uri=filename_path,
            matches=[
                Document(text=f'the person is {p}')
                for p in (
                        'pretty',
                        'ugly',
                )
            ],
        )
    ]
)

text_and_scores = r['@m', ['text', 'scores__clip_score__value']]
st.write(text_and_scores)
