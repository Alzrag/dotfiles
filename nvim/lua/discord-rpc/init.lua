local Discord = require("discord-rpc.discord")
local client_id = "1491289624860033034" -- paste yours here
local client = Discord:new(client_id)

local function update_activity()
  local filename = vim.fn.expand("%:t")
  local filetype = vim.bo.filetype

  local details = filename ~= "" and ("Editing " .. filename) or "In Neovim"

  local state = filetype ~= "" and ("Filetype: " .. filetype) or vim.fn.expand("%:~")

  client:set_activity(details, state)
end

client:connect(function()
  update_activity()
end)

vim.api.nvim_create_autocmd({ "BufEnter", "BufAdd" }, {
  callback = update_activity,
})

vim.api.nvim_create_autocmd("VimLeavePre", {
  callback = function()
    client:clear_activity()
    client:disconnect()
  end,
})
