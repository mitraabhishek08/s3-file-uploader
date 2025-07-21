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

def copy_button(url, key):
    button_html = f"""
    <div style="display: flex; align-items: center;">
        <input type="text" value="{url}" id="input_{key}" readonly style="width:80%; margin-right: 10px;"/>
        <button onclick="
            navigator.clipboard.writeText(document.getElementById('input_{key}').value);
            this.innerText='Copied!';
            setTimeout(() => {{ this.innerText='Copy'; }}, 2000);
        ">Copy</button>
    </div>
    """
    components.html(button_html, height=40)

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

    # Mandatory folder input
    folder_name = st.text_input(f"Folder name under '{BUCKET_NAME}/{BASE_FOLDER}' (required):").strip()
    
    uploaded_files = st.file_uploader(
        "Upload one or more images",
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
        accept_multiple_files=True
    )

    if st.button("Upload"):
        # Check mandatory folder name
        if not folder_name:
            st.error("Please enter a valid folder name.")
            return
        
        if not uploaded_files:
            st.warning("Please upload at least one image before clicking Upload.")
            return

        urls = []
        for file in uploaded_files:
            # Create S3 key as abmitra/folder_name/filename
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