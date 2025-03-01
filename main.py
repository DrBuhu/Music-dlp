from bandcamp_api import Bandcamp

bc = Bandcamp()

album = bc.get_album(album_url="https://c418.bandcamp.com/album/minecraft-volume-alpha")
print(response.text)  # Check what the response contains


print("Album title:", album.album_title)
