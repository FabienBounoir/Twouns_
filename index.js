const tmi = require('tmi.js'); // pour utiliser l'API Twitch
const fs = require('fs'); // pour enregistrer le texte dans un fichier
const filteredBot = require('./filteredBot.json');

//get file in directory
const channels = fs.readdirSync('./logoChannel').filter(file => file.endsWith('.png')).map(file => file.replace('.png', ''))

// Connexion à l'API Twitch
const client = new tmi.Client({
    options: { debug: false, },
    connection: {
        reconnect: true,
        secure: true
    },
    channels: channels // récupération des chaînes à écouter
});

// Enregistrement des messages de tchat dans un fichier
client.on('message', (channel, tags, message, self) => {
    if (self) return; // ignore les messages envoyés par le bot lui-même
    let date = new Date(); // récupération de la date

    if (filteredBot.includes(tags.username) || (tags.username == (channel.replace("#", "")))) return; // ignore les messages envoyés par les bots filtrés
    fs.appendFileSync(`./tchatTranscript/chat-${channel}-${date.getMonth()}-${date.getFullYear()}.txt`, `${message}\n`); // enregistrement du message dans un fichier
    fs.appendFileSync(`./tchatUser/pseudo-${channel}-${date.getMonth()}-${date.getFullYear()}.txt`, `${tags.username}\n`); // enregistrement du nom d'utilisateur dans un fichier
});

// Connexion au client
client.connect();