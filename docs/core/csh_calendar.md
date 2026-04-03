This core component is used for all the fetching, formatting and structuring for the CSH calendar portion of Jumpstart.

---

### Yielding

During a fetch of the calendar, if any other clients attempt to connect, they will be yielding async until the initial calendar cache has returned.

---

### Documentation Overview
::: core.cshcalendar