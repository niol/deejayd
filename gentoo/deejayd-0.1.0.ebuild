# Copyright 1999-2007 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

inherit distutils

DESCRIPTION="deejayd is a media player daemon based on twisted."
HOMEPAGE="http://mroy31.dyndns.org/~roy/projects/deejayd"
SRC_URI="http://mroy31.dyndns.org/~roy/archives/deejayd/${P}.tar.gz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~x86"
IUSE="mad vorbis webradio"

DEPEND=">=virtual/python-2.4"

RDEPEND="${DEPEND}
	>=dev-python/twisted-2.0.0
	>=dev-python/pygtk-2.8
	>=dev-python/pysqlite-2.2
	>=media-libs/mutagen-1.9
	>=media-libs/gst-plugins-good-0.10.2
	>=dev-python/gst-python-0.10.2
	mad? ( >=media-plugins/gst-plugins-mad-0.10.2 )
	vorbis? ( >=media-plugins/gst-plugins-vorbis-0.10.2
		>=media-plugins/gst-plugins-ogg-0.10.2 )
	webradio? ( >=media-plugins/gst-plugins-gnomevfs-0.10.2 )"

pkg_setup() {
	enewuser deejayd '' '' "/var/lib/deejayd" audio || die "problem adding user deejayd"

	# also change the homedir if the user has existed before
	usermod -d "/var/lib/deejayd" deejayd
}

src_install() {
	python setup.py install || die

	# Pid File
	dodir /var/run/deejayd
	fowners deejayd:audio /var/run/deejayd
	fperms 750 /var/run/deejayd
	keepdir /var/run/deejayd

	# Conf
	insinto /etc
	newins doc/deejayd.conf.example deejayd.conf

	diropts -m0755 -o deejayd -g audio
	dodir /var/lib/deejayd/music
	keepdir /var/lib/deejayd/music
	dodir /var/lib/deejayd/mediadb
	keepdir /var/lib/deejayd/mediadb

	# Log
	dodir /var/log/deejayd
	keepdir /var/log/deejayd
}
