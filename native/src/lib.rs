use jni::objects::JClass;
use jni::sys::jstring;
use jni::JNIEnv;

#[no_mangle]
pub extern "system" fn Java_com_mimax_lu_NativeBridge_engineVersion(
    mut env: JNIEnv,
    _class: JClass,
) -> jstring {
    env.new_string("Mi_Max Rust Engine 0.1.0").unwrap().into_raw()
}
