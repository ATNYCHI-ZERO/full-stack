# Provenance Checklist & GPG/Git Commands

This checklist outlines the steps to establish a secure and verifiable provenance chain for the code and specifications, as referenced in the HYBRID-KEM v1 spec.

## 1. Create repository and initial commit
```bash
git init
git add .
git commit -m "Initial Crown-KEM spec commit"
```

## 2. Create a GPG key (example, Linux)
```bash
gpg --full-generate-key
```

Choose Ed25519 or RSA 4096 and follow the prompts. Use the identity `Brendon Joseph Kelly (Atnychi)` with the email `crownmathematics@protonmail.com`.

List the key and export the public component for verifiers:
```bash
gpg --list-secret-keys --keyid-format LONG
gpg --armor --export YOURKEYID > publickey.asc
```

Distribute `publickey.asc` to allow others to verify your signatures.

## 3. Configure Git and sign commits/tags
```bash
# Tell git which key to use
git config --global user.signingkey YOURKEYID
# Sign all commits by default
git config --global commit.gpgsign true

# Sign a commit (if not default)
git commit -S -m "Sign initial commit"

# Create a signed tag for the release
git tag -a v1.0 -m "Crown-KEM v1" -s
```

## 4. Push to remote
```bash
git remote add origin git@github.com:YourHandle/Crown-KEM.git
git push -u origin main --tags
```

## 5. Create signed distribution artifacts

Produce a `.tar.gz` archive of the release tag and a detached signature file:
```bash
git archive --format=tar --prefix=Crown-KEM/ v1.0 | gzip > Crown-KEM-v1.0.tar.gz
gpg --armor --detach-sign Crown-KEM-v1.0.tar.gz
```

## 6. Timestamp options

* **Notarize** the SOL v1.0 PDF with a local notary and archive the scan in the repository.
* **Anchor** the commit hash to a public timestamp (for example, by embedding it into a blockchain transaction). Consider the legal implications of the chosen anchor.
