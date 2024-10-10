## v0.5.3 (2024-10-10)

### Fix

- **docker**: fix dockerfile

## v0.5.2 (2024-10-10)

### Fix

- improve logging of scheduler

## v0.5.1 (2024-08-26)

### Fix

- **scheduler**: improve logging

## v0.5.0 (2024-08-26)

### Feat

- support backup/restore from postrgres dbs (#6)

## v0.4.1 (2024-04-01)

### Fix

- **restore**: chown root restore directory

## v0.4.0 (2024-04-01)

### Feat

- **restore**: optionally chown restored files

### Fix

- **restore**: add 5 second pause

## v0.3.0 (2024-03-27)

### Feat

- **backup**: regex to include or exclude files from backup

### Fix

- **logging**: enque concurrent log requests
- **cron**: increase jitter to 10 minutes
- **restore**: delete all files from dest before restore

## v0.2.0 (2024-03-26)

### Feat

- **backup**: exclude specific files

## v0.1.3 (2024-03-26)

### Fix

- increase compression level

## v0.1.2 (2024-03-26)

### Fix

- **docker**: fix command

## v0.1.1 (2024-03-26)

### Fix

- **docker**: set container timezone with `TZ`

## v0.1.0 (2024-03-26)

### Feat

- initial commit
