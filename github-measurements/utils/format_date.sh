#!/bin/bash
###
# Remove letters Z and T in time prefixe in lines.
# Changes lines like:
# 2017-08-17T00:00:00Z,Q0pS2uiu3kTDnVwFWYCKRw,jA8E_-3-tyToWXcng4fdvw,PushEvent
# to:
# 2017-08-17T00:00:00Z,Q0pS2uiu3kTDnVwFWYCKRw,jA8E_-3-tyToWXcng4fdvw,PushEvent 
###
# Options:
# <filename>
sed -i 's/^\(2017-[[:digit:]]\{2\}-[[:digit:]]\{2\}\)T\(.\{8\}\)Z/\1 \2/'
