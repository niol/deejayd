<?xml version="1.0" encoding="utf-8" ?>
<project name="Deejayd_webui" default="build" basedir=".">
  <!-- Arguments to gwtc and devmode targets -->
  <property name="gwt.args" value="" />

  <!-- Configure path to GWT SDK -->
  <property name="gwt.sdk" location="TO BE COMPLETED" />

  <path id="project.class.path">
    <pathelement location="war/WEB-INF/classes"/>
    <pathelement location="${gwt.sdk}/gwt-user.jar"/>
    <fileset dir="${gwt.sdk}" includes="gwt-dev*.jar"/>
    <!-- Add any additional non-server libs (such as JUnit) -->
    <!-- <fileset dir="war/WEB-INF/lib" includes="**/*.jar"/> -->
  </path>

  <target name="javac" description="Compile java source">
    <mkdir dir="war/WEB-INF/classes"/>
    <javac srcdir="src" includes="**" encoding="utf-8"
        destdir="war/WEB-INF/classes"
        source="1.5" target="1.5" nowarn="true"
        debug="true" debuglevel="lines,vars,source">
      <classpath refid="project.class.path"/>
    </javac>
    <copy todir="war/WEB-INF/classes">
      <fileset dir="src" excludes="**/*.java"/>
    </copy>
  </target>

  <target name="build" depends="javac" description="Build this project (Dev)">
    <java failonerror="true" fork="true" classname="com.google.gwt.dev.Compiler">
      <classpath>
        <pathelement location="src"/>
        <path refid="project.class.path"/>
      </classpath>
      <!-- add jvmarg -Xss16M or similar if you see a StackOverflowError -->
      <jvmarg value="-Xmx256M"/>
      <!-- Additional arguments like -style PRETTY or -logLevel DEBUG -->
      <arg line="${gwt.args}"/>
      <arg value="org.mroy31.deejayd.webui.Deejayd_webui"/>
      <arg value="org.mroy31.deejayd.mobile.Mobile_Webui"/>
    </java>
  </target>

  <target name="builddist" depends="javac" description="Build this project (Dev)">
    <mkdir dir="../build/webui/"/>
    <java failonerror="true" fork="true" classname="com.google.gwt.dev.Compiler">
      <classpath>
        <pathelement location="src"/>
        <path refid="project.class.path"/>
      </classpath>
      <!-- add jvmarg -Xss16M or similar if you see a StackOverflowError -->
      <jvmarg value="-Xmx256M"/>
      <!-- Additional arguments like -style PRETTY or -logLevel DEBUG -->
      <arg line="${gwt.args} -war ../build/webui/"/>
      <arg value="org.mroy31.deejayd.webui.Deejayd_webui"/>
      <arg value="org.mroy31.deejayd.mobile.Mobile_Webui"/>
    </java>
  </target>

  <target name="clean" description="Cleans this project">
    <delete dir="war/WEB-INF/classes" failonerror="false" />
    <delete dir="war/deejayd_webui" failonerror="false" />
    <delete dir="war/mobile_webui" failonerror="false" />
  </target>

</project>