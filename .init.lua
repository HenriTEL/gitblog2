-- special script called by main redbean process at startup
HidePath('/usr/share/zoneinfo/')
HidePath('/usr/share/ssl/')
function OnHttpRequest()
  path = GetPath()
  if not RoutePath(path) then
    path = path .. '.html'
    ServeAsset(path)
  end
end