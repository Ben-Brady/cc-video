local requests = {}
local HTTP_SERVER = "http://localhost:8000"
local WS_SERVER = "ws://localhost:8000"

-- 5BwygBWGhRQ

---@param display MonitorDisplay
local function generateDisplayString(display)
    return string.format("%d-%d-%d-%d", display.rows, display.cols, display.width, display.height)
end

---@param id string
---@param display MonitorDisplay
---@return string
function requests.createYoutubeStream(id, display)
    local display_str = generateDisplayString(display)
    local url = HTTP_SERVER .. "/start/youtube?id=" .. id .. "&display=" .. display_str
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
---@param display MonitorDisplay
---@return string
function requests.createFileStream(filename, display)
    local display_str = generateDisplayString(display)
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

---@param display MonitorDisplay
---@return string
function requests.createLiveStream(display)
    local display_str = generateDisplayString(display)
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

---@param display MonitorDisplay
---@return string
function requests.downloadTestImage(display)
    local display_str = generateDisplayString(display)
    local url = HTTP_SERVER .. "/image/test?display=" .. display_str
    local r, msg = http.get(url)
    if r == nil then
        error(msg)
    end

    local data = r.readAll()
    if data == nil then
        error("No data from " .. url)
    end

    return data
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
