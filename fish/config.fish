if status is-interactive
    # Commands to run in interactive sessions can go here
end

# Show system info at terminal launch
if status is-interactive
    fastfetch
end


# Pyenv setup for fish
set -Ux PYENV_ROOT $HOME/.pyenv
set -Ux PATH $PYENV_ROOT/bin $PATH
status --is-interactive; and pyenv init --path | source
status --is-interactive; and pyenv init - | source
