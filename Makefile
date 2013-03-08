# variables to use sandboxed binaries
#PIP := PIP_DOWNLOAD_CACHE=$${HOME}/.pip_download_cache env/bin/pip
PIP := env/bin/pip
NOSE := env/bin/nosetests
PY := env/bin/python

# -------- Environment --------
# env is a folder so no phony is necessary
env:
	virtualenv env

.PHONY: deps
deps: env packages/.done
	# see http://tartley.com/?p=1423&cpage=1
	# --upgrade needed to force local (if there's a system install)
	$(PIP) install --upgrade --no-index --find-links=file://$${PWD}/packages -r requirements.txt

packages/.done:
	mkdir packages; \
	$(PIP) install --download packages -r requirements.txt;\
	touch packages/.done

# rm_env isn't a file so it needs to be marked as "phony"
.PHONY: rm_env
rm_env:
	rm -rf env


# --------- Dev --------------------
.PHONY: dev
dev: deps
	$(PY) setup.py develop


# --------- Testing ----------
.PHONY: test
test: deps $(NOSE)
	$(NOSE)

# nose depends on the nosetests binary
$(NOSE): packages/.done-nose
	$(PIP) install --upgrade --no-index --find-links=file://$${PWD}/packages nose

packages/.done-nose:
	# need to drop this marker. otherwise it
	# downloads everytime
	$(PIP) install --download packages nose;\
	touch packages/.done-nose



# --------- PyPi ----------
.PHONY: build
build: env
	$(PY) setup.py sdist

.PHONY: upload
upload: env
	$(PY) setup.py sdist register upload

.PHONY: clean
clean:
	rm -rf dist *.egg-info
