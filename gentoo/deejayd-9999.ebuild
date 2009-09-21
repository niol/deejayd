# Copyright 1999-2008 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

NEED_PYTHON=2.4
inherit distutils darcs

DESCRIPTION="deejayd is a media player daemon based on twisted."
HOMEPAGE="http://mroy31.dyndns.org/~roy/projects/deejayd"
#SRC_URI="http://mroy31.dyndns.org/~roy/archives/deejayd/${P}.tar.gz"
EDARCS_REPOSITORY="http://mroy31.dyndns.org/~roy/repository/deejayd"
EDARCS_LOCALREPO="deejayd"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~x86 ~amd64"
IUSE="sqlite mysql webradio xine gstreamer webui inotify logrotate man"

DEPEND="
	man? ( >=app-text/docbook-xsl-stylesheets-1.73
	       >=dev-libs/libxslt-1.1.24 )"
RDEPEND="
	>=dev-python/twisted-2.0.0
	sqlite? ( || ( >=dev-lang/python-2.5.0
	             >=dev-python/pysqlite-2.2 ) )
	mysql? ( >=dev-python/mysql-python-1.2.1 )
	|| ( >=dev-lang/python-2.5.0
		 >=dev-python/celementtree-1.0.2 )
	|| ( >=dev-lang/python-2.6.0
		 >=dev-python/simplejson-2.0.9 )
	>=media-libs/mutagen-1.9
	>=dev-python/kaa-metadata-1.1
	>=dev-python/lxml-1.3.0
	logrotate? ( app-admin/logrotate )
	webui?
        (
            >=dev-python/twisted-web-0.6.0
        )
	inotify? ( >=dev-python/pyinotify-0.6.0 )
	gstreamer?
		(
			>=dev-python/pygobject-2.14
			>=media-libs/gstreamer-0.10.2
			>=media-libs/gst-plugins-base-0.10.2
			>=media-libs/gst-plugins-good-0.10.2
			>=dev-python/gst-python-0.10.2
			>=media-plugins/gst-plugins-meta-0.10-r1
			webradio? ( >=media-plugins/gst-plugins-gnomevfs-0.10.2 )
		)
	xine? ( || ( >=dev-lang/python-2.5.0
	             >=dev-python/ctypes-1.0.0 )
			>=x11-libs/libX11-1.0.0
			>=x11-libs/libXext-1.0.0
			>=media-libs/xine-lib-1.1.0 )"


pkg_setup() {
	enewuser deejayd '' '' "/var/lib/deejayd" audio,cdrom || die "problem adding user deejayd"

	# also change homedir and groups if the user has existed before
	usermod -d "/var/lib/deejayd" -G audio,cdrom deejayd
}

src_install() {
	${python} setup.py install --root=${D} --no-compile "$@" || die

	# Pid File
	dodir /var/run/deejayd
	fowners deejayd:audio /var/run/deejayd
	fperms 750 /var/run/deejayd
	keepdir /var/run/deejayd

	# Conf
	insinto /etc
	newins deejayd/ui/defaults.conf deejayd.conf

	# conf.d
	newconfd "${FILESDIR}/deejayd.confd" deejayd
	fperms 600 /etc/conf.d/deejayd
	# init.d
	newinitd "${FILESDIR}/deejayd.init" deejayd

	diropts -m0755 -o deejayd -g audio
	dodir /var/lib/deejayd/music
	keepdir /var/lib/deejayd/music
	dodir /var/lib/deejayd/video
	keepdir /var/lib/deejayd/video

	# Log
	dodir /var/log/deejayd
	keepdir /var/log/deejayd

	# Logrotate support
	if use logrotate ; then
		insinto /etc/logrotate.d
		newins "${FILESDIR}/deejayd.logrotate" deejayd
	fi
}
