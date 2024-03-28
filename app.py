import os
from email import encoders
import subprocess
import sys
from pytube import YouTube
import moviepy.editor as mp 
import zipfile
import streamlit as st
import email, smtplib, ssl
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from youtube_search import YoutubeSearch

# def download_video(singer, num_videos, output_dir):
#     print(f"Downloading {num_videos} videos of {singer}...")
#     try:
#         os.makedirs(output_dir, exist_ok=True)
        
#         # Search for videos using YoutubeSearch
#         results = YoutubeSearch(singer + " songs", max_results=num_videos).to_dict()
        
#         downloaded = 0
#         for video in results:
#             if downloaded >= num_videos:
#                 break
#             try:
#                 yt = YouTube("https://www.youtube.com" + video['url_suffix'])
#                 stream = yt.streams.filter(only_audio=True).first()
#                 if stream:
#                     stream.download(output_dir)
#                     downloaded += 1
#                     print(f"Downloading video {downloaded}...")
#                 else:
#                     print(f"No available audio stream for video {video['title']}")
#             except Exception as e:
#                 print(f"Error downloading video {video['title']}: {e}")
        
#         print("Download complete.")
#     except Exception as e:
#         print(f"Error downloading videos: {e}")
#         sys.exit(1)

def download_video(singer, num_videos, output_dir):
    print(f"Downloading {num_videos} videos of {singer}...")
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Search for videos using YoutubeSearch
        results = YoutubeSearch(singer + " songs", max_results=num_videos).to_dict()
        
        downloaded = 0
        for video in results:
            if downloaded >= num_videos:
                break
            try:
                yt = YouTube("https://www.youtube.com" + video['url_suffix'])
                stream = yt.streams.filter(only_audio=True).first()
                if stream:
                    stream.download(output_dir)
                    downloaded += 1
                    print(f"Downloading video {downloaded}...")
                else:
                    print(f"No available audio stream for video {video['title']}")
            except Exception as e:
                print(f"Error downloading video {video['title']}: {e}")
        
        print("Download complete.")
    except Exception as e:
        print(f"Error downloading videos: {e}")
        sys.exit(1)


def cut_audio(input_dir, output_dir, duration):
    print(f"Cutting first {duration} seconds of audio...")
    try:
        os.makedirs(output_dir, exist_ok=True)
        for filename in os.listdir(input_dir):
            if filename.endswith(".mp3"):
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, filename.replace(".mp3", "_cut.mp3"))
                subprocess.run(["ffmpeg", "-ss", "00:00:00", "-t", str(duration), "-i", input_path, "-acodec", "copy", output_path], check=True)
        print("Cutting complete.")
    except Exception as e:
        print(f"Error cutting audio: {e}")
        sys.exit(1)
        
def merge_audio(input_dir, output_file):
    print("Merging audio files...")
    try:
        with open(output_file, "wb") as outfile:
            for file in os.listdir(input_dir):
                if file.endswith(".mp3"):
                    with open(os.path.join(input_dir, file), "rb") as infile:
                        outfile.write(infile.read())
        print("Merging complete.")
    except Exception as e:
        print(f"Error merging audio files: {e}")
        sys.exit(1)

def convert_to_audio(input_dir, output_dir):
    print("Converting videos to audio...")
    try:
        os.makedirs(output_dir, exist_ok=True)
        for filename in os.listdir(input_dir):
            if filename.endswith(".mp4"):
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, filename.replace(".mp4", ".mp3"))
                subprocess.run(["ffmpeg", "-i", input_path, "-vn", "-acodec", "libmp3lame", "-y", output_path], check=True)
        print("Conversion complete.")
    except Exception as e:
        print(f"Error converting videos to audio: {e}")
        sys.exit(1)


def main(singer, num_videos, cut_duration, output_file, email):
    input_dir = "temp_videos"
    output_dir = "temp_audio"

    download_video(singer, num_videos, input_dir)
    convert_to_audio(input_dir, output_dir)
    cut_audio(output_dir, output_dir, cut_duration)
    merge_audio(output_dir, output_file)

    # Clean up temporary directories
    os.system(f"rm -rf {input_dir}")
    os.system(f"rm -rf {output_dir}")

    # Zip the audio file
    zip_file = output_file + ".zip"
    with zipfile.ZipFile(zip_file, 'w') as zipObj:
        zipObj.write(output_file)

    # Send email with the zip file attached
    send_email(email, zip_file)

    print("Mashup complete!")

def send_email(receiver_email, attachment_path):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "averma3_be21@thapar.edu"  # Enter your email address
    password = "bads opsw ssss tcru"  # Enter your email password

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Your Mashup Audio File!"

    # Add body to email
    message.attach(MIMEText("Your mashup has been created. Please find the attached zip file.", "plain"))

    # Open and attach the zip file
    with open(attachment_path, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
    
    # Encode file in ASCII characters to send by email    
    encoders.encode_base64(part)
    
    # Add header with the filename
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {attachment_path}",
    )
    
    # Add attachment to message
    message.attach(part)
    
    # Create a secure SSL context
    context = ssl.create_default_context()
    
    # Send email
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

if __name__ == "__main__":
    st.title("Mashup Web Service")
    st.write("Enter the details below to create a mashup and receive it via email.")

    form = st.form(key='my_form')

    name = form.text_input(label='Enter singer name') 
    output_file = form.text_input(label='Enter output file name')
    num_videos =  form.number_input(label='Enter number of videos', min_value=1, step=1)
    cut_duration = form.number_input(label='Enter cut duration in seconds', min_value=1, step=1)
    email = form.text_input(label='Enter your email-id')
    submit_button = form.form_submit_button(label='Submit')

    if submit_button:
        if not name or not output_file or not email:
            st.warning('Please enter all the required fields!')
        else:
            st.success('Mashup request submitted successfully! Please wait for the email with the mashup file.')

            # Call main function to create mashup and send email
            main(name, num_videos, cut_duration, output_file, email)
