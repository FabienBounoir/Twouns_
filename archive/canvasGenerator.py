import os
import re
import tkinter as tk
import requests

from collections import Counter
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from enum import Enum


class Folder(Enum):
    EMOTE = "emote"
    TCHAT = "tchat"
    USER = "user"


channel = "mastu"

# load_dotenv()


def get_font_size(text, max_font_size):
    font = ImageFont.truetype("../assets/Oswald.ttf", size=max_font_size)

    while font.getlength(text) > 380:
        max_font_size -= 1
        font = ImageFont.truetype("../assets/Oswald.ttf", size=max_font_size)

    return font


def set_token_twitch():
    # Remplacez 'YOUR_CLIENT_ID' et 'YOUR_CLIENT_SECRET' par les valeurs appropriées
    client_id = 'm63ye9823waz6kanq4ipipulhjugiy'
    client_secret = 'egadk14esjej99f4ltdg6px9n0zukg'

    # client_id = os.getenv("TWITCH_CLIENT_ID")
    # client_secret = os.getenv("TWITCH_CLIENT_SECRET")

    # URL de l'endpoint Twitch pour obtenir un jeton d'accès
    token_url = f"https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials"

    try:
        # Effectuer la demande POST pour obtenir le jeton d'accès
        response = requests.post(token_url)
        response.raise_for_status()

        # Obtenir les informations du jeton d'accès à partir de la réponse JSON
        info_token = response.json()

        # Définir le jeton Twitch dans l'objet client
        return info_token["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"Erreur : {e}")


token_twitch = set_token_twitch()


def get_twitch_profile_picture(username):
    # client_id = os.getenv("TWITCH_CLIENT_ID")
    client_id = 'm63ye9823waz6kanq4ipipulhjugiy'

    # Define the Twitch API URL
    url = f'https://api.twitch.tv/helix/users?login={username}'

    # Set up the headers with your Client ID and Client Secret
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {token_twitch}'
    }

    try:
        # Make a GET request to the Twitch API
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        # Get the user's profile picture URL from the response
        profile_picture_url = data['data'][0]['profile_image_url']

        response = requests.get(profile_picture_url)

        # Vérifiez si le téléchargement s'est bien passé (statut 200)
        if response.status_code == 200:
            # Obtenez le contenu de l'image
            image_avatar = Image.open(BytesIO(response.content))

            nouvelle_taille = (
                145, int(image_avatar.height * (145 / image_avatar.width)))
            image_avatar = image_avatar.resize(nouvelle_taille)

            return image_avatar
        else:
            raise Exception("Erreur lors du téléchargement de l'image.")

    except Exception as e:
        image_avatar = Image.open("../assets/defaultAvatar.png")

        nouvelle_taille = (
            145, int(image_avatar.height * (145 / image_avatar.width)))
        image_avatar = image_avatar.resize(nouvelle_taille)

        return image_avatar


def getText(folder, channel):
    print("📝 Récupération "+folder+" pour la chaine " + channel)
    texte = ""

    # Récupérer les textes
    with open("../"+folder+"/"+channel+".txt", "r") as f:
        texte += f.read()

    return texte


def getCountAndSize(text, top, split):
    arrayElement = text.split(split)
    arrayElement.pop()

    arrayCounter = Counter(arrayElement)

    sorted_emotes = sorted(arrayCounter.items(),
                           key=lambda x: x[1], reverse=True)

    size = len(sorted_emotes)
    sorted_emotes = sorted_emotes[:top]

    return sorted_emotes, size


emoteText = getText(Folder.EMOTE.value, channel)
userText = getText(Folder.USER.value, channel)
messageText = getText(Folder.TCHAT.value, channel)


if (emoteText == ""):
    print("❌ No text found for " + channel_name)
    exit()

# Récupérer les emotes, users et messages
emoteArray, emoteSize = getCountAndSize(emoteText, 5, ",")
userArray, userSize = getCountAndSize(userText, 5, "\n")
messageArray, messageSize = getCountAndSize(messageText, 5, "\n")


largeur, hauteur = 2836, 1690
image = Image.new('RGBA', (largeur, hauteur), color='#101010')

# Chargez une image existante
templateImage = Image.open('../assets/template.png')

# Collez l'image sur l'image principale à une position spécifique
image.paste(templateImage, (0, 0))
draw = ImageDraw.Draw(image)

couleur_texte = (255, 255, 255)

for emote_id, count in emoteArray:
    print("🔎 Emote: " + emote_id)
    # Récupérer l'emote
    url_emote = "https://static-cdn.jtvnw.net/emoticons/v2/" + \
        emote_id.split("#")[1]+"/static/dark/3.0"
    response = requests.get(url_emote)

    # Vérifiez si le téléchargement s'est bien passé (statut 200)
    if response.status_code == 200:
        # Obtenez le contenu de l'image
        image_emote = Image.open(BytesIO(response.content))

        nouvelle_taille = (
            145, int(image_emote.height * (145 / image_emote.width)))
        image_emote = image_emote.resize(nouvelle_taille)

        # Collez l'image de l'emote sur l'image principale à une position spécifique
        position_x, position_y = 229, 404 + \
            (emoteArray.index((emote_id, count)) * 145 +
             62 * emoteArray.index((emote_id, count)))

        try:
            image.paste(image_emote, (position_x, position_y), image_emote)
        except:
            image.paste(image_emote, (position_x, position_y))

        draw.text((1250, position_y+(145/2)),
                  "Envoyée " + str(count) + " fois", font=ImageFont.truetype("../assets/Oswald.ttf", size=70), fill=couleur_texte, anchor="rm")
    else:
        print("Erreur lors du téléchargement de l'image " + emote_id)


for user, count in userArray:
    print("👤 User: " + user)

    # Récupérer l'emote
    image_avatar = get_twitch_profile_picture(user)

    position_x, position_y = 1589, 404 + \
        (userArray.index((user, count)) * 145 +
         62 * userArray.index((user, count)))

    image.paste(image_avatar, (position_x, position_y))

    font = get_font_size(user, 60)

    draw.text((position_x + 170, position_y+(145/2)), user,
              font=font, fill=couleur_texte, anchor="lm")

    draw.text((2608, position_y+(145/2)),
              str(count) + " Messages", font=ImageFont.truetype("../assets/Oswald.ttf", size=70), fill=couleur_texte, anchor="rm")


# Ajoutez le texte à l'image
draw.text((1418, 1530),
          f"{messageSize} messages ont été envoyés par {userSize} personnes",
          font=ImageFont.truetype("../assets/Oswald.ttf", size=80), fill=couleur_texte, anchor="mm")

image.save('image_finale.png')
