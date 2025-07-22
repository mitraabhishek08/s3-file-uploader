import streamlit as st
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
    # Use Streamlit columns for layout
    col1, col2 = st.columns([5, 1])
    with col1:
        st.text_input(f"Image URL", value=url, key=f"url_{key}", disabled=True)
    with col2:
        if st.button("Copy", key=f"copy_{key}"):
            st.experimental_set_query_params()  # workaround to trigger rerun before JS
            st.toast("Copied to clipboard!", icon="✅")
            # Use Streamlit's clipboard copy with JS through components
            js = f"""
            <script>
            navigator.clipboard.writeText("{url}");
            </script>
            """
            st.components.v1.html(js)
            

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
