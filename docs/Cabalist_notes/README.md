Setup instructions:

Requirements:
Android Phone
ADB tools

Enable Bluetooth HCI Snoop


# Misc Notes
Register for the app.   Google Translate on another phone is really helpful.   This login will get you into the Template editor as well

Nothing seems very secure at all.   It appears that I can see and read all other tags (but not write to them without being in BT range).  SQL injections look like a strong possibility.


# TODO: Insert adding tag to app instructions


Some important links:

# Original app location
https://www.gicisky.net/app/ble-app-release-v3.0.13.apk
https://www.gicisky.net/app/ble-app-release-v3.0.24.apk  # <- much more responsive version of the app

# Template Editor
http://a.picksmart.cn:8081



4.2 Screen is 400x300


Forward Slashes (/) are illegal in template names but it doesn't stop you from putting them in

235 lines are Black & White
235 lines are Red
Lines are 512px long.  This requires 234.375 lines of data on the 4.2 inch screen
The last line will be 192 pixels long. Confirmed
The lines don't appear to be linked in any way.

Compression (or whatever is happening) is only happening on a per line basis.

See the annotated lines in `successful_img_captures/` for a breakdown of what is currently known.
##### Max length of GH markdown color line is 339 (no including markers) 