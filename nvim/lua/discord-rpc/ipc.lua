local M = {}

function M.get_socket_path()
  local os_name = vim.loop.os_uname().sysname

  if os_name == "Windows_NT" then
    return [[\\.\pipe\discord-ipc-0]]
  elseif os_name == "Darwin" then
    local tmpdir = os.getenv("TMPDIR") or "/tmp"
    return tmpdir .. "/discord-ipc-0"
  else
    local xdg = os.getenv("XDG_RUNTIME_DIR")
    local path = xdg and (xdg .. "/discord-ipc-0") or "/tmp/discord-ipc-0"
    --vim.schedule(function()
    --vim.notify("discord-rpc: looking for socket at " .. path)
    --end)
    return path
  end
end

local function pack_int32(n)
  return string.char(
    bit.band(n, 0xFF),
    bit.band(bit.rshift(n, 8), 0xFF),
    bit.band(bit.rshift(n, 16), 0xFF),
    bit.band(bit.rshift(n, 24), 0xFF)
  )
end

function M.encode(opcode, payload)
  local body = vim.fn.json_encode(payload)
  local header = pack_int32(opcode) .. pack_int32(#body)
  return header .. body
end

function M.decode(chunk)
  if #chunk < 8 then
    return nil
  end
  local body = chunk:sub(9)
  local ok, result = pcall(vim.json.decode, body)
  if ok then
    return result
  end
  return nil
end

return M
