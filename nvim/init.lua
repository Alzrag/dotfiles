-- bootstrap lazy.nvim, LazyVim and your plugins
require("config.lazy")
require("discord-rpc")
vim.env.NVIM_LISTEN_ADDRESS = vim.fn.expand("$XDG_RUNTIME_DIR/nvimsocket")
