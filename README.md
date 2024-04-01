# Plex_Scrobble_App (PSA)
App to have a more full-featured music scrobbling with Plex, LastFM, ListenBrainz

## Setup
This is the most base Docker command with the easy way to connect to Plex.  
If you don't want to use ListenBrainz or Last.fm, just remove their variables.  
```
docker run \
   --name plex_scrobble_app \
   -e PLEX_USERNAME=your_plex_username_here \
   -e LB_API_TOKEN=listen_brainz_api_token_here_optional \
   -e LFM_API_KEY=lastfm_api_key_here_optional \
   -e LFM_API_SECRET=lastfm_api_secret_here_optional \
   -e LFM_USERNAME=lastfm_username_here_optional \
   -e LFM_PASSWORD=lastfm_password_here_optional \
   -p 1841:1841 \
   plex_scrobble_app:latest
```

### Setup Advanced
This method requires more stuff but increases correct matches.  

**Plex URL and Token:**  
[How can I find my Plex token?](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)
```
docker run \
   --name plex_scrobble_app \
   -e ADVANCED=TRUE \
   -e LOGIN_METHOD=URL_TOKEN \
   -e PLEX_URL=http://plex_ip_address_here:32400 \
   -e PLEX_TOKEN=your_plex_token_here \
   -e PLEX_USERNAME=your_plex_username_here \
   -e LB_API_TOKEN=listen_brainz_api_token_here_optional \
   -e LFM_API_KEY=lastfm_api_key_here_optional \
   -e LFM_API_SECRET=lastfm_api_secret_here_optional \
   -e LFM_USERNAME=lastfm_username_here_optional \
   -e LFM_PASSWORD=lastfm_password_here_optional \
   -p 1841:1841 \
   plex_scrobble_app:latest
```

**Plex Username, Password and Server Name:**  
This method is slow to authenticate. It is recommended to use `URL_TOKEN`  
```docker run \
   --name plex_scrobble_app \
   -e ADVANCED=TRUE \
   -e LOGIN_METHOD=USER_PASS_SERVER \
   -e PLEX_URL=http://plex_ip_address_here:32400 \
   -e PLEX_USERNAME=your_plex_username_here \
   -e PLEX_PASSWORD=your_plex_password_here \
   -e PLEX_SERVER_NAME=your_plex_server_name_here
   -e LB_API_TOKEN=listen_brainz_api_token_here_optional \
   -e LFM_API_KEY=lastfm_api_key_here_optional \
   -e LFM_API_SECRET=lastfm_api_secret_here_optional \
   -e LFM_USERNAME=lastfm_username_here_optional \
   -e LFM_PASSWORD=lastfm_password_here_optional \
   -p 1841:1841 \
   plex_scrobble_app:latest
```


