#!/bin/bash

slack-cleaner --token $SLACK_BOT_TOKEN --message --channel schedule --user "bandeirastime-bot" --perform --bot --as_user
