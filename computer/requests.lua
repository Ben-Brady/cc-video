local display = require("display")

local requests = {}
local HTTP_SERVER = "http://localhost:8000"
local WS_SERVER = "ws://localhost:8000"

-- 5BwygBWGhRQ

---@param id string
---@return string
function requests.createYoutubeStream(id)
    local display_str = display.getDisplayString()
    local url = HTTP_SERVER .. "/start/youtube?id=" .. id .. "&display=" .. display_str
    print(url)
    local r, msg = http.get(url)
    if r == nil then
        error(msg)
    end

    local data = r.readAll()
    if data == nil then
        error("No data from " .. url)
    end

    local stream_id = textutils.unserialiseJSON(data)
    ---@cast stream_id string

    return stream_id
end

---@param filename string
---@return string
function requests.createFileStream(filename)
    local display_str = display.getDisplayString()
    local url = HTTP_SERVER .. "/start/file?filename=" .. filename .. "&display=" .. display_str
    local r, msg = http.get(url)
    if r == nil then
        error(msg)
    end

    local data = r.readAll()
    if data == nil then
        error("No data from " .. url)
    end

    local stream_id = textutils.unserialiseJSON(data)
    ---@cast stream_id string

    return stream_id
end

---@return string
function requests.createLiveStream()
    local display_str = display.getDisplayString()
    local url = HTTP_SERVER .. "/start/stream?display=" .. display_str
    local r, msg = http.get(url)
    if r == nil then
        error(msg)
    end

    local data = r.readAll()
    if data == nil then
        error("No data from " .. url)
    end

    local stream_id = textutils.unserialiseJSON(data)
    ---@cast stream_id string

    return stream_id
end

---@param stream_id string
---@return Websocket
function requests.connectToVideoStream(stream_id)
    local ws, msg = http.websocket(WS_SERVER .. "/stream/video?id=" .. stream_id)
    if not ws then
        error(msg)
    end
    return ws
end

---@param stream_id string
---@return Websocket | nil
function requests.connectToAudioStream(stream_id)
    local ws = http.websocket(WS_SERVER .. "/stream/audio?id=" .. stream_id)
    return ws or nil
end

return requests
