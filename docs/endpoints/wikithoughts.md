## Wiki Thoughts Endpoints

### Overview

This is a builtin API from MediaWiki and allows us to pull sections from the Wiki that are formatted in a certain way. See Wiki Thoughts Core for more info.

### Authentication

The MediaWiki API requires authentication in the form of a bot user. Credentials can be made [here](https://wiki.csh.rit.edu/wiki/Special:BotPasswords). You will also have to specify a category to pull from the Wiki, which for jumpstart is "Jumpstart Curated".

### Error Handling

In the event of an Error, the API will log an error and display default text

```json
{
  "WARNING": "508 Bot is not authenticated, cancelling fetch of category pages"
}
```

::: api.endpoints.wikithought
