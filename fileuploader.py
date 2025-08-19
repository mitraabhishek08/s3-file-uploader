import streamlit as st
import streamlit.components.v1 as components
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

AWS_ACCESS_KEY = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
BUCKET_NAME = 'mdm-presales-assets'
BASE_FOLDER = 'abmitra'
CLOUDFRONT_URL_PREFIX = 'https://d1zuq1scot7wwi.cloudfront.net/'

s3 = boto3.client('s3',
                  aws_access_key_id=AWS_ACCESS_KEY,
                  aws_secret_access_key=AWS_SECRET_KEY)

def list_s3_folders(bucket, prefix):
    """List 'folders' (common prefixes) under an S3 prefix."""
    try:
        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix + '/',
            Delimiter='/'
        )
    except ClientError as e:
        st.sidebar.error(f"Failed to list folders: {e}")
        return []

    folders = []
    if 'CommonPrefixes' in response:
        for cp in response['CommonPrefixes']:
            folder_name = cp['Prefix'].rstrip('/').split('/')[-1]
            folders.append(folder_name)
    return folders

def list_s3_files(bucket, prefix):
    """List all files under a given S3 prefix."""
    try:
        paginator = s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix + '/')
    except ClientError as e:
        st.error(f"Failed to list files: {e}")
        return []

    files = []
    for page in page_iterator:
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                if not key.endswith('/'):  # exclude folder keys
                    files.append(key)
    return files

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
    st.title("S3 Media Manager")

    # Fetch existing folders once
    existing_folders = list_s3_folders(BUCKET_NAME, BASE_FOLDER)

    st.sidebar.markdown("### Select folder")
    selected_folder = st.sidebar.selectbox(
        "Select a folder:",
        options=[""] + existing_folders,
        index=0
    )

    # Contact info below in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        **Contact:**  
        For any questions or feedback, please email me at  
        <a href="mailto:abmitra@informatica.com">abmitra@informatica.com</a>  
        <br>
        Or ping me directly on Microsoft Teams:  
        <a href="https://teams.microsoft.com/l/chat/0/0?users=abmitra@informatica.com" target="_blank">Chat on Teams</a>
        """,
        unsafe_allow_html=True
    )

    # Synchronize selected folder to text input
    folder_name = st.text_input(
        label="Enter folder name (*):",
        value=selected_folder,
        help=f"This folder will be created under '{BUCKET_NAME}/{BASE_FOLDER}'.",
        key="folder_name_input"
    ).strip()

    st.info("_This folder name will reuse an existing folder if present, or create a new one. If you are going to use the generated url(s) with URL type field, make sure not to use any space in the folder name and/or in the uploaded image name._")

    # Button to load and view existing images
    view_images = st.button("View Images")

    # Placeholder for existing images
    images_placeholder = st.empty()

    if view_images:
        if not folder_name:
            st.error("Please select or enter a valid folder name to view images.")
        else:
            with images_placeholder.container():
                st.subheader(f"Existing images in folder '{folder_name}':")
                files = list_s3_files(BUCKET_NAME, f"{BASE_FOLDER}/{folder_name}")
                if not files:
                    st.write("No images found in this folder.")
                else:
                    for idx, s3_key in enumerate(files):
                        url = CLOUDFRONT_URL_PREFIX + s3_key
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            st.image(url, width=60)
                        with col2:
                            copy_button(url, idx)

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
                col1, col2 = st.columns([1, 5])
                with col1:
                    st.image(url, width=60)
                with col2:
                    copy_button(url, idx)

if __name__ == "__main__":
    main()
