# -*- coding:utf-8 -*-

import hashlib
import json
from textwrap import dedent
from time import time
from uuid import uuid4
from flask import *
from urllib.parse import urlparse


class BlockChain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.new_block(previous_hash='1', proof=100)
        self.nodes = set()

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipent, amount):
        self.current_transactions.append({
            'sender': sender,
            'recipent': recipent,
            'amount': amount
        })
        return self.last_block['index'] + 1

    def proof_of_work(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    def register_node(self, address):
        parsed_url = urlparse(address)

        self.nodes.add(parsed_url.netloc)

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1
        while (current_index < len(chain)):

            block = chain[current_index]

            if block['previous_hash'] != self.hash(last_block):
                return False
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            last_block = block
            current_index += 1
        return True

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]


app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
blockchain = BlockChain()


@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    blockchain.new_transaction(
        sender='0',
        recipent=node_identifier,
        amount=1
    )

    previous_hash = blockchain.hash(last_block)

    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': 'New block Forged',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']

    }

    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount']

    if values is not None and not all(k in values for k in required):
        return 'Missing values', 400

    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    response = {'message': f'Transactions will be added to Block {index}'}

    return jsonify(response), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
