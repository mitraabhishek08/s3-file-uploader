import streamlit as st
import streamlit.components.v1 as components
import boto3
from botocore.exceptions import NoCredentialsError

AWS_ACCESS_KEY = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
BUCKET_NAME = 'mdm-presales-assets'
BASE_FOLDER = 'abmitra'
CLOUDFRONT_URL_PREFIX = 'https://d1zuq1scot7wwi.cloudfront.net/'

s3 = boto3.client('s3',
                  aws_access_key_id=AWS_ACCESS_KEY,
                  aws_secret_access_key=AWS_SECRET_KEY)

def copy_button(url: str, idx: int):
    button_html = f"""
    <style>
        .copy-container {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }}
        .copy-input {{
            width: 90%;
            padding: 6px 8px;
            font-size: 14px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-right: 8px;
        }}
        .copy-btn {{
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 6px 12px;
            font-size: 14px;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }}
        .copy-btn:hover {{
            background-color: #45a049;
        }}
        .copied-msg {{
            color: #4CAF50;
            font-weight: 600;
            margin-left: 10px;
            display: none;
            user-select: none;
        }}
    </style>
    <div class="copy-container">
        <input class="copy-input" type="text" value="{url}" id="copyInput{idx}" readonly />
        <button class="copy-btn" onclick="
            const copyText = document.getElementById('copyInput{idx}');
            navigator.clipboard.writeText(copyText.value);
            const msg = document.getElementById('copiedMsg{idx}');
            msg.style.display = 'inline';
            setTimeout(() => {{ msg.style.display = 'none'; }}, 2000);
        ">Copy</button>
        <span id="copiedMsg{idx}" class="copied-msg">Copied!</span>
    </div>
    """
    components.html(button_html, height=50)


def upload_to_s3(file, key):
    try:
        s3.upload_fileobj(file, BUCKET_NAME, key)
        return True
    except NoCredentialsError:
        st.error("AWS credentials not available.")
        return False
    except Exception as e:
        st.error(f"Failed to upload {key}: {e}")
        return False

def main():
    st.title("Image Uploader to S3 Bucket")

    st.sidebar.markdown("---")  # Horizontal separator in sidebar

    st.sidebar.markdown(
        """
        **Contact:**  
        For any questions or feedback, please email me at  
        <a href="mailto:abmitra@informatica.com">abmitra@informatica.com</a>
        """,
        unsafe_allow_html=True
)


    # Mandatory folder input
    folder_name = st.text_input(label="Enter folder name:",
    help=f"This folder will be created under '{BUCKET_NAME}/{BASE_FOLDER}'",
    key="folder_name_input").strip()
    st.info("This folder name will reuse an existing folder if present, or create a new one.")

    uploaded_files = st.file_uploader(
        "Upload one or more images",
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
        accept_multiple_files=True
    )

    if st.button("Upload"):
        if not folder_name:
            st.error("Please enter a valid folder name.")
            return

        if not uploaded_files:
            st.warning("Please upload at least one image before clicking Upload.")
            return

        urls = []
        for file in uploaded_files:
            s3_key = f"{BASE_FOLDER}/{folder_name}/{file.name}"
            success = upload_to_s3(file, s3_key)
            if success:
                url = f"{CLOUDFRONT_URL_PREFIX}{BASE_FOLDER}/{folder_name}/{file.name}"
                urls.append(url)

        if urls:
            st.success("Upload completed!")
            st.write("Final URLs:")
            for idx, url in enumerate(urls):
                copy_button(url, idx)

if __name__ == "__main__":
    main()
