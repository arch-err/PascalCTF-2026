# Geoguesser

## Description
> *Alan Spendaccione accumulated so much debts that he travelled far away to escape Fabio Mafioso, join the mafia and help Fabio catch Alan!*
>
> *The flag format is `pascalCTF{YY.YY,XX.XX}` where Y=latitude and X=longitude, round the numbers down.*

**Files:** [challenge.png](./orig/challenge.png)

## Solution
**TL;DR**: Notice the beauty salon *"Sedalicious"* in the background -> google -> google maps -> coords
1. Image shows a street scene with Mediterranean architecture
2. I quickly noticed the text on one of the buildings in the in the background. Since they love to mention Malta in these challenges that narrowed the search down quite a lot! Searching around for "Malta Sedalicie" (couldn't read the rest), quickly gave me [sedalicious.com](https://sedalicious.com/booking/). Their logo also match the one in the image.
3. Luckily for me, sedalicious only exists in one place, so a quick google street view to confirm the location also gave me the coordinates to construct the final flag!

### Flag
> `pascalCTF{35.92,14.47}`
