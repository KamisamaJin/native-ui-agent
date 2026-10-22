#!/usr/bin/env python3
"""Verify the preimplementation adapter inventory in addition to gate members."""
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
def main():
 freeze=ex.read(R/'operators/preimplementation-adapter-freeze.json')
 for rel,expected in freeze['files'].items():assert ex.sha(R/rel)==expected,rel
 print('PASS unchanged preimplementation shared adapters:',len(freeze['files']))
if __name__=='__main__':main()
