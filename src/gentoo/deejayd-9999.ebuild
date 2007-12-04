# Copyright 1999-2007 Gentoo Foundation
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
IUSE="dvd mad vorbis webradio xine gstreamer X ffmpeg webui"

DEPEND=" xine? (>=dev-python/pyrex-0.9.4.0
		>=dev-util/pkgconfig-0.20
		>=x11-libs/libXext-1.0.3
		>=media-libs/xine-lib-1.1.0)"

RDEPEND="${DEPEND}
	>=dev-python/twisted-2.0.0
	>=dev-python/pysqlite-2.2
	>=dev-python/celementtree-1.0.2
	>=media-libs/mutagen-1.9
	webui? ( >=dev-python/twisted-web-0.6.0 )
	gstreamer? ( >=dev-python/pygtk-2.8
		>=media-libs/gstreamer-0.10.2
		>=media-libs/gst-plugins-base-0.10.2
		>=media-libs/gst-plugins-good-0.10.2
		>=dev-python/gst-python-0.10.2
		ffmpeg? ( >=media-plugins/gst-plugins-ffmpeg-0.10.2 )
		mad? ( >=media-plugins/gst-plugins-mad-0.10.2 )
		dvd?
			(
				>=media-plugins/gst-plugins-a52dec-0.10
				>=media-plugins/gst-plugins-mpeg2dec-0.10
				>=media-libs/gst-plugins-ugly-0.10
				>=media-plugins/gst-plugins-dvdread-0.10
			)
		vorbis? ( >=media-plugins/gst-plugins-vorbis-0.10.2
			>=media-plugins/gst-plugins-ogg-0.10.2 )
		webradio? ( >=media-plugins/gst-plugins-gnomevfs-0.10.2 ))
	dvd? ( >=media-video/lsdvd-0.16 )"
S="${WORKDIR}/${P}/src"


pkg_setup() {
	if use gstreamer && use X && ! built_with_use 'media-libs/gst-plugins-base' 'X' ; then
		einfo "Build gst-plugins-base with the X useflag"
		einfo "echo \"media-libs/gst-plugins-base X\">>/etc/portage/package.use"
		einfo "emerge -1 gst-plugins-base"
		die "gst-plugins-base requires X useflag"
	fi

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
	newins doc/deejayd.conf.example deejayd.conf

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
	dodir /var/lib/deejayd/mediadb
	keepdir /var/lib/deejayd/mediadb

	# Log
	dodir /var/log/deejayd
	keepdir /var/log/deejayd
}
