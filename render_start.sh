#!/bin/bash
echo "Starting Daphne server on port $PORT..."
echo "Waiting for proper initialization..."
sleep 3
echo "Starting Daphne with verbose logging..."
exec daphne -b 0.0.0.0 -p $PORT -v 2 PublicBridge.asgi:application