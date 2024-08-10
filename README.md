# SigSpy
Realtime signal plotting

## Dependencies
Developed with Python 3.11

Package
- pyserial
- dearpygui (1.11.1)

## Support

So far, only support the following transport and protocol.

Transport:
- serial port com

Protocol:
- line by line, utf-8 encoded, CSV
    - (example 3 signals) 
    - "S0n, S1n, S2n \r\n 
    - S0n+1, S1n+1, S2n+1 \r\n"

## Usage

python main.py
