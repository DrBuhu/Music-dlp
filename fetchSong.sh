function downloadSong {
    output=$(yt-dlp --embed-thumbnail \
        -x -S acodec:aac,proto \
        --compat-opt filename-sanitization \
        --embed-metadata \
        --cookies-from-browser firefox \
        --match-filters "title!=More" \
        --print "%(title)s" \
	--print "%(author)s" \
        "https://youtu.be/SQE32uhmxMg?si=nGpK-eUw9dal3jPT")
    
    title=$(echo "$output" | sed -n '1p')
    author=$(echo "$output" | sed -n '2p')
}

downloadSong

echo "title: $title"
echo "author: $author"

function getTags() {

}
