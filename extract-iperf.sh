sed -i 1,+5d "$1"
sed -i '$d' "$1"
cat "$1" | cut -c 7-11 > b
sed -i 's/-//g' b
cat "$1" | cut -c 22-27 > c
sed -i 's/M//g' c
sed -i 's/B//g' c
paste b c > d
rm -rf b c
