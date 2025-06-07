#!/bin/bash
set -e

API_URL="https://cloud-init.dev.itlusions.com"
MAC_ADDRESS=$(ip link show | awk '/ether/ {print $2}' | head -n 1)
SERIAL=$(dmidecode -s system-uuid)
BIOS_VENDOR=$(dmidecode -s bios-vendor)
BIOS_VERSION=$(dmidecode -s bios-version)
BIOS_RELEASE_DATE=$(dmidecode -s bios-release-date)
BIOS_REVISION=$(dmidecode -s bios-revision)

# Check if tpm2-tools is installed
if ! dpkg -l | grep -qw tpm2-tools; then
    echo "tpm2-tools is not installed. Installing..."
    if [ -x "$(command -v apt)" ]; then
        sudo apt update && sudo apt install -y tpm2-tools
    elif [ -x "$(command -v yum)" ]; then
        sudo yum install -y tpm2-tools
    else
        echo "Package manager not supported. Please install tpm2-tools manually."
        exit 1
    fi
fi

# Check if jc is installed
if ! dpkg -l | grep -qw jc; then
    echo "jc is not installed. Installing..."
    if [ -x "$(command -v apt)" ]; then
        sudo apt update && sudo apt install -y jc
    elif [ -x "$(command -v yum)" ]; then
        sudo yum install -y jc
    else
        echo "Package manager not supported. Please install jc manually."
        exit 1
    fi
fi

# Function to convert dmidecode output to JSON
convert_dmidecode_to_json() {
    sudo dmidecode | awk '
        BEGIN { section = ""; print "{" }
        /^[^\t]/ { 
            if (section != "") { print "}," }
            section = $0
            gsub(/ /, "_", section)
            print "\"" section "\": {"
        }
        /^\t/ {
            key = $1
            value = substr($0, index($0, $2))
            gsub(/:/, "", key)
            gsub(/ /, "_", key)
            gsub(/"/, "\\\"", value)
            print "\"" key "\": \"" value "\","
        }
        END { print "}}" }
    ' | sed 's/,}/}/g'  # Remove trailing commas
}

# Save dmidecode output as JSON
echo "Converting dmidecode output to JSON..."
DMIDECODE_JSON=$(dmidecode | jc --dmidecode -p)

# Create TPM credentials
tpm2_createek --ek-context /tmp/ek.ctx
tpm2_createak --ek-context /tmp/ek.ctx --ak-context /tmp/ak.ctx \
 --public /tmp/ak.pub --ak-name /tmp/ak.name --ak-auth "" --hash-algorithm sha256

# Quote with TPM
NONCE=$(openssl rand -hex 16)
tpm2_quote --key-context /tmp/ak.ctx --pcr-list sha256:0,1,2,3,4,5,6,7 \
  --message /tmp/quote.bin --qualification "$NONCE" \
  --signature /tmp/sig.bin --hash-algorithm sha256

QUOTE=$(base64 -w 0 /tmp/quote.bin)
SIG=$(base64 -w 0 /tmp/sig.bin)
AIK_PUB=$(base64 -w 0 /tmp/ak.pub)

echo "Enter one-time registration token (optional): "
read REG_TOKEN

# Build JSON payload
PAYLOAD=$(jq -n \
  --arg serial "$SERIAL" \
  --arg bios "$BIOS_VENDOR" \
  --arg version "$BIOS_VERSION" \
  --arg quote "$QUOTE" \
  --arg nonce "$NONCE" \
  --arg aik "$AIK_PUB" \
  --arg sig "$SIG" \
  --arg reg "$REG_TOKEN" \
  --argjson dmi "$DMIDECODE_JSON" \
  '{ serial_number: $serial, bios_vendor: $bios, bios_version: $version, registration_token: $reg,
     tpm: { quote: $quote, nonce: $nonce, aik_pub: $aik, signature: $sig, expected_hash: "" },
     dmi_data: $dmi }')

echo "Payload to be sent:"
echo "$PAYLOAD"

# POST to /bootstrap
# Uncomment the following lines to send the payload to the API
# curl -X POST "$API_URL/bootstrap" \
#   -H "Content-Type: application/json" \
#   -H "mac: $MAC_ADDRESS" \
#   -d "$PAYLOAD"