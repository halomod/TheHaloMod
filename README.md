# TheHaloMod

**The web-app for calculating Halo Model quantities.**

This is the source code for [TheHaloMod](http://hmf.icrar.org), which uses
the [hmf](https://github.com/steven-murray/hmf) and [halomod](https://github.com/steven-murray/halomod)
Python package to calculate halo model quantities.

The web-app is powered by [Django](https://www.djangoproject.com/) and uses
[Bootstrap 4](https://getbootstrap.com/) as a CSS framework.

To acknowledge use of this app, cite
[Murray, Power & Robotham (2013)](http://adsabs.harvard.edu/abs/2013A%26C.....3...23M").

This app began as `HMFcalc` back in 2013, and has been thoroughly reworked and expanded
to provide full halo model capabilities.

## Contributing

Clearly, this repository is intended for developers (users shouldn't need to see this
code, or I've done something wrong!). I would *love* contributions to this app from the
community -- whether in the form of bug reports, feature requests, or new code.
Please consider getting involved!

If you'd like to get involved but have never done any web-development before (like me
when I started this project), I'd suggest taking the
[Django Beginner's Tutorial](https://docs.djangoproject.com/en/3.0/intro/tutorial01/) to
wrap your head around things a bit.

After that, here's a bit of a primer of how this repo is laid out:

The top-level is reserved for interesting project-level stuff like this README, and
scripts for managing the website itself (things you call manually when you're on the
server, outside the context of the web-app itself).

The [TheHaloMod](TheHaloMod/) directory contains the website-level settings and structure (eg.
where urls point to).

The [templates](templates/) directory contains the HTML files (really, they're just
kinda-sorta HTML, they're actually templates) that define how each page of the website
will be structured (and often, the text on the website).

Finally, the most important directory: [halomod_app](halomod_app/).
This contains the logic of the web-application, as a bunch of python files.
Most important here are the `views.py`,
which defines the various things that happen when different URLs are accessed (not
always a web-page opening -- sometimes a download of a file, or a form displaying etc.),
and the `forms.py` which defines the (fairly large) form into which inputs for the
HMF are given.

### Running the Server Locally

To set up locally, you should install `poetry`, then run `poetry install` in the
top-level directory. This will install all dependencies.
To add another dependency, run `poetry add <dep>` then make sure you do
`poetry export -f requirements.txt -o requirements.txt` and commit the output file.

To run the dev server, you should simply have to do  `docker-compose -f compose-dev.yml up --build`.
This should open a browser at the correct address.

There are `.envs/base` and `.envs/local` files that are read, and do _not_ contain any
sensitive information (in production, there are other files here that do have sensitive
info, and are not stored in VCS). You may modify these if need be.

## Deployment

I'm gonna use this space to remind _myself_ how I go about deployment for `TheHaloMod`.
For local dev, just use the above instructions.

To deploy:

1. Make a branch
2. Make some changes
3. Commit
4. Push to github
5. Ensure everything's working, then merge to master
6. Log in to the server (`galileo.sese.asu.edu`)
7. Do a git pull in the repo
8. Run `ENV=env/test PORT=8010 docker-compose -f compose-prod.yml up --build` to
   build the test server.
9. (Manually!) go to the test server and make sure things are OK.
10. Run `ENV=env/production PORT=8000 docker-compose -f compose-prod.yml up --build` to
    build the production server.

Secret settings are set in the `.envs/` directory, and not kept in VCS for obvious reasons.
This `.env/` directory _is_ in the repo on the server itself, and my local copy on my
own computer. In order to keep it safe, it's also backed up. The different compose files
essentially just take different `.envs/` files in, and set a couple of different env
variables.

Some things to do if the actual server has to be changed:

1. Fix up the references to SSL certificates in `nginx/default.conf`
2. Need to copy the local versions of `.envs/test` and `.envs/production` onto the
   server.
