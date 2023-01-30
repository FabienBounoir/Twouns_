import os
from dotenv import load_dotenv

import re
import tweepy
import numpy as np
import matplotlib.pyplot as plt


from PIL import Image
from datetime import datetime, timedelta
from scipy.ndimage import gaussian_gradient_magnitude
from wordcloud import WordCloud, ImageColorGenerator

months = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]

# load env variables
print("✅ Load env variables")
load_dotenv()

# Twitter API credentials
consumer_key = os.getenv("API_KEY")
consumer_secret = os.getenv("API_SECRET_KEY")
access_token = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

# Authentification
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
print("✅ Authentification Twitter")


d = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()

transcript_path = os.path.join(d, "./../tchatTranscript/")
files = os.listdir(transcript_path)

now = datetime.now()

month_ago = now - timedelta(days=now.day)

month = month_ago.strftime("%m")
year = month_ago.strftime("%Y")

print("✅ Generate Image for " + month + "_" + year)

for file in files:
    print("_________________________________________________________")

    twitter_name = ""

    # get the channel name
    match = re.search(r"chat-#(.*?)\.", file)
    if match == None:
        print("❌ File " + file + " is not a chat transcript file")
        continue

    channel_name = match.group(1)

    print("✅ Generate Image for " + channel_name + "chat...")

    # load chat transcript text file
    text = open(
        os.path.join(d, "./../tchatTranscript/" + file), encoding="utf-8"
    ).read()

    logo_path = os.path.join(d, "./../logoChannel/")
    logo_files = os.listdir(logo_path)

    file_logo = ""

    for logo_file in logo_files:
        if logo_file.find(channel_name) != -1:
            twitter_name = logo_file.split("-")[1].split(".")[0]
            logo_color = np.array(Image.open(os.path.join(d, logo_path + logo_file)))

    for file_name in os.listdir(logo_path):
        if file_name.startswith(channel_name):
            print("✅ Logo found: " + file_name)
            file_logo = file_name
            break

    if file_logo == "":
        print("❌ No logo found for " + channel_name)
        continue

    logo_color = np.array(Image.open(os.path.join(d, logo_path + file_logo)))
    print("✅ Logo color generated for " + channel_name)

    # subsample by factor of 3. Very lossy but for a wordcloud we don't really care.
    logo_color = logo_color[::3, ::3]

    # create mask  white is "masked out"
    logo_mask = logo_color.copy()
    logo_mask[logo_mask.sum(axis=2) == 0] = 255
    print("✅ Logo mask generated for " + channel_name)

    # some finesse: we enforce boundaries between colors so they get less washed out.
    # For that we do some edge detection in the image
    edges = np.mean(
        [gaussian_gradient_magnitude(logo_color[:, :, i] / 255.0, 2) for i in range(3)],
        axis=0,
    )
    print("✅ Logo edges generated for " + channel_name)

    logo_mask[edges > 0.08] = 255

    # create wordcloud. A bit sluggish, you can subsample more strongly for quicker rendering
    # relative_scaling=0 means the frequencies in the data are reflected less
    # acurately but it makes a better picture
    wc = WordCloud(
        max_words=10000,
        mask=logo_mask,
        max_font_size=20,
        random_state=42,
        relative_scaling=0,
    )
    print("✅ Wordcloud generated for " + channel_name)

    # generate word cloud
    wc.generate(text)
    plt.imshow(wc)

    # create coloring from image
    image_colors = ImageColorGenerator(logo_color)
    wc.recolor(color_func=image_colors)
    plt.figure(figsize=(10, 10))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    wc.to_file("./image/" + channel_name + "-" + month + "_" + year + ".png")
    print("✅ Image saved for " + channel_name)

    if channel_name == "":
        continue

    # Envoi d'un tweet
    api.update_status_with_media(
        "@"
        + twitter_name
        + " Voici le récapitulatif du mois de "
        + months[int(month) - 1]
        + " "
        + year
        + " sur ton chat https://www.twitch.tv/"
        + channel_name
        + " !",
        "image.png",
        file=open("./image/" + channel_name + "-" + month + "_" + year + ".png", "rb"),
    )

    print("✅ Tweet sent for " + channel_name)

# if os.path.exists("./../tchatTranscript/" + file):
#     os.remove("./../tchatTranscript/" + file)
#     print("✅ File " + file + " deleted")
# else:
#     print(f"{'./../tchatTranscript/'+file} n'existe pas")

# plt.figure(figsize=(10, 10))
# plt.title("Original Image")
# plt.imshow(logo_color)

# plt.figure(figsize=(10, 10))
# plt.title("Edge map")
# plt.imshow(edges)
# plt.axis("off")
# plt.show()
