.PHONY: conformance
conformance:
	cd packages/conformance && npm install && npm run generate && npm test
