local ipc = require("discord-rpc.ipc")

local Discord = {}
Discord.__index = Discord

local OPCODES = {
  handshake = 0,
  frame = 1,
}

function Discord:new(client_id)
  local o = {
    client_id = client_id,
    pipe = nil,
    ready = false,
  }
  setmetatable(o, self)
  return o
end

function Discord:connect(on_ready)
  local socket_path = ipc.get_socket_path()
  self.pipe = vim.loop.new_pipe(false)

  --vim.notify("discord-rpc: attempting connect to " .. socket_path)

  local handshake = ipc.encode(OPCODES.handshake, {
    v = 1,
    client_id = self.client_id,
  })

  self.pipe:connect(socket_path, function(err)
    if err then
      --vim.schedule(function()
      --vim.notify("discord-rpc: connect failed: " .. tostring(err), vim.log.levels.ERROR)
      --end)
      return
    end

    --vim.schedule(function()
    --vim.notify("discord-rpc: pipe connected, sending handshake")
    --end)

    self.pipe:write(handshake)

    self.pipe:read_start(function(read_err, chunk)
      if read_err then
        --vim.schedule(function()
        --vim.notify("discord-rpc: read error: " .. tostring(read_err), vim.log.levels.ERROR)
        --end)
        return
      end
      if not chunk then
        --vim.schedule(function()
        --vim.notify("discord-rpc: pipe closed with no data", vim.log.levels.WARN)
        --end)
        return
      end

      local msg = ipc.decode(chunk)
      --vim.schedule(function()
      --vim.notify("discord-rpc: received message evt=" .. tostring(msg and msg.evt))
      --end)

      if msg and msg.evt == "READY" then
        self.ready = true
        vim.schedule(function()
          --vim.notify("discord-rpc: connected and ready!")
          if on_ready then
            on_ready()
          end
        end)
      end
    end)
  end)
end

function Discord:set_activity(details, state)
  --if not self.ready then
  --vim.notify("discord-rpc: set_activity called but not ready", vim.log.levels.WARN)
  --return
  --end

  local payload = {
    cmd = "SET_ACTIVITY",
    nonce = tostring(math.random(1000000)),
    args = {
      pid = vim.loop.os_getpid(),
      activity = {
        details = details,
        state = state,
        timestamps = {
          start = os.time(),
        },
      },
    },
  }

  local msg = ipc.encode(OPCODES.frame, payload)
  self.pipe:write(msg)
end

function Discord:clear_activity()
  if not self.ready then
    return
  end

  local payload = {
    cmd = "SET_ACTIVITY",
    nonce = tostring(math.random(1000000)),
    args = {
      pid = vim.loop.os_getpid(),
      activity = vim.NIL,
    },
  }

  self.pipe:write(ipc.encode(OPCODES.frame, payload))
end

function Discord:disconnect()
  self.ready = false
  if self.pipe and not self.pipe:is_closing() then
    self.pipe:shutdown()
    self.pipe:close()
  end
end

return Discord
