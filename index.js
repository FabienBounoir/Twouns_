const tmi = require('tmi.js'); // pour utiliser l'API Twitch
const fs = require('fs'); // pour enregistrer le texte dans un fichier
const filteredBot = require('./filteredBot.json');

//get file in directory
const channels = fs.readdirSync('./logoChannel').filter(file => file.endsWith('.png')).map(file => file.split("-")[0])

// Connexion à l'API Twitch
const client = new tmi.Client({
    options: { debug: false, },
    connection: {
        reconnect: true,
        secure: true
    },
    channels: ["bounsbot"] //channels // récupération des chaînes à écouter
});

// Enregistrement des messages de tchat dans un fichier
client.on('message', (channel, tags, message, self) => {
    if (self) return; // ignore les messages envoyés par le bot lui-même

    channel = channel.replace("#", "")

    if (filteredBot.includes(tags.username) || (tags.username == channel)) return; // ignore les messages envoyés par les bots filtrés
    fs.appendFileSync(`./tchat/${channel}.txt`, `${message}\n`); // enregistrement du message dans un fichier
    fs.appendFileSync(`./user/${channel}.txt`, `${tags.username}\n`); // enregistrement du nom d'utilisateur dans un fichier

    if (channel == "squeezie") {
        let date = new Date();

        if (date.getDate() == "9") {
            fs.appendFileSync(`./tchat/gpexplorer.txt`, `${message}\n`); // enregistrement du message dans un fichier
            fs.appendFileSync(`./user/gpexplorer.txt`, `${tags.username}\n`); // enregistrement du nom d'utilisateur dans un fichier
        }
    }
});

//https://static-cdn.jtvnw.net/emoticons/v1/emotesv2_3f327a65f575466f88ea00ffc74c98de/4.0

client.on('join', (channel, username, self) => {
    if (self) return; // ignore les messages envoyés par le bot lui-même

    channel = channel.replace("#", "")
    console.log(channel, username)

    if (filteredBot.includes(username) || (username == channel)) return; // ignore les messages envoyés par les bots filtrés
    fs.appendFileSync(`./user/${channel}.txt`, `${username}\n`); // enregistrement du nom d'utilisateur dans un fichier
});

// Connexion au client
client.connect();