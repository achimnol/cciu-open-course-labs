# Developer Guidelines #

## Coding Convention ##
Basically we follow [conventions of Django](http://docs.djangoproject.com/en/dev/internals/contributing/#coding-style) and [PEP8](http://www.python.org/dev/peps/pep-0008/) with a few exceptions/additions.

  * You don't have to put a blank line between different kinds of imports.
  * You don't have to put spaces at the beggining and ending of template variable replacer. (In other words, `{{myvar}}` is allowed as well as `{{ myvar }}`)
  * Put always `# -*- coding: utf-8 -*-` at the top of every python source files.
  * Always use UTF-8 encoding for every text files in this project.

For Vim users, you may put the following settings to your vimrc for PEP8-style indenting:
```
filetype plugin on
inoremap # X^H#    " NOTE: ^H is a visual character (Ctrl+V, Ctrl+H)
```
and create `{UserDir}/.vim/ftplugin/python.vim` in UNIX-like OSes and `{UserDir}/vimfiles/ftplugin/python.vim` in Windows with the following content:
```
setlocal sts=4 st=4 sw=4 expandtab
setlocal formatoptions=croql
setlocal nocindent nocopyindent si ai
```