Jumpstart has many different themes displayed on the website, this is a step by step process on how to implement your own!

**Any images that need to be added should be put in src/static/img**

### Adding Background

1. Go to the file: **src/static/js/main.js**
2. In the function long update, figure out the day, month, and hour of your theme.
    - hour is in 24H format
3. Add it into the if statement (please change this in the future)
    - Make sure it follows the bgImage = "url(../static/img/{**YOUR FILE HERE**})"

### Adding CSS Theme
1. Go to the file **src/static/css/style.css**
2. Add a new class for the colors **MAKE SURE IT STARTS WITH {theme-}!!!**
3. Change the colors in this new class
4. Repeat the steps in the "Adding Background"
5. Add a new index into "allThemes" with your css theme, along with any changes to weatherwidget or datadog
6. change the themeToLoad in the if statement to load your new index



