CHANGES
=======

0.4.1 (2019-03-19)
------------------

- Fix: Text following a comment tag was discarded.

- Fix: 3+ whitespace was replaced with nothing. Caused text to miss spaces.


0.4.0 (2018-01-23)
------------------

- More indentation fixes.

- Added support for O format lists (First, Second, Third)

- Add support to have bullet lists in numebr lists and vice versa

- Convert tables in lists to lists in lists

- Support for blockSpan in table styles.

- Handle tail text of comments

- Supporting RML blockSpan styles for tables

- Take the maximum, not the first when calculating the number of columns


0.3.0 (2018-01-12)
------------------

- Many many formatting fixes including an almost complete rewrite of
  list handling and list styles.


0.2.0 (2017-12-08)
------------------

- Cleaned up the public API.

- Added basic docs.


0.1.0 (2017-11-21)
------------------

- Basic Support for:

  * Flowables: para, blockTable, hr, ul, ol

  * Stylesheets: paraStyle

  * Page Layout

- Initial Release
