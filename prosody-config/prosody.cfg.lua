admins = { }

modules_enabled = {
    "roster";
    "saslauth";
    "disco";
    "private";
    "vcard";
    "version";
}

-- Autoriser la création de comptes (utile en dev)
allow_registration = true

-- Authentification locale avec base d'utilisateurs interne
authentication = "internal_plain"

-- PAS d'obligation de chiffrement TLS pour les clients
c2s_require_encryption = false

-- Autoriser l'authentification PLAIN même sans TLS (SEULEMENT POUR DEV !)
allow_unencrypted_plain_auth = true

VirtualHost "xmpp"
